; benchmark generated from python API
(set-info :status unknown)
(declare-fun c () (_ BitVec 8))
(declare-fun b () (_ BitVec 8))
(declare-fun a () (_ BitVec 8))
(assert
 (let ((?x28 (bvmul ((_ extract 7 0) (ite (bvslt a (_ bv0 8)) (bvneg a) a)) ((_ zero_extend 5) ((_ extract 2 0) b)))))
(let ((?x29 ((_ extract 7 0) ?x28)))
(let (($x19 (and (distinct (ite (= (ite (bvsgt (_ bv253 8) a) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) true)))
(let ((?x21 (ite (and (and (distinct (ite (bvsgt (_ bv4 8) a) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) true) $x19) (_ bv1 1) (_ bv0 1))))
(let (($x32 (and (distinct ?x21 (_ bv0 1)) true)))
(let ((?x63 (ite $x32 (bvadd ((_ extract 7 0) ((_ extract 7 0) ((_ extract 7 0) c))) ((_ extract 7 0) ((_ extract 7 0) ?x29))) c)))
(and (distinct (ite $x32 (bvadd ?x29 ((_ extract 7 0) c)) c) ?x63) true))))))))
(check-sat)
