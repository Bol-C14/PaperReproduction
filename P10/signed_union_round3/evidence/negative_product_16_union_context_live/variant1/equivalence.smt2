; benchmark generated from python API
(set-info :status unknown)
(declare-fun c () (_ BitVec 16))
(declare-fun a () (_ BitVec 16))
(declare-fun b () (_ BitVec 16))
(assert
 (let ((?x22 ((_ zero_extend 2) ((_ extract 2 0) ((_ extract 15 0) ((_ extract 15 0) (ite (bvslt a (_ bv0 16)) (bvneg a) a)))))))
(let ((?x90 ((_ zero_extend 11) (bvmul ((_ zero_extend 2) ((_ extract 2 0) ((_ extract 2 0) ((_ extract 2 0) ((_ extract 2 0) b))))) ?x22))))
(let (($x18 (and (distinct (ite (= (ite (bvsgt (_ bv65532 16) a) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) true)))
(let ((?x20 (ite (and (and (distinct (ite (bvsgt (_ bv0 16) a) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) true) $x18) (_ bv1 1) (_ bv0 1))))
(let (($x23 (and (distinct ?x20 (_ bv0 1)) true)))
(let ((?x80 ((_ extract 15 0) (ite (bvslt a (_ bv0 16)) (bvneg a) a))))
(and (distinct (ite $x23 (bvmul ?x80 ((_ zero_extend 13) ((_ extract 2 0) b))) c) (ite $x23 ?x90 c)) true))))))))
(check-sat)
