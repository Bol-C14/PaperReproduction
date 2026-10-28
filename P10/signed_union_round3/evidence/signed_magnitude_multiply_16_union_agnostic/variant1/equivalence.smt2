; benchmark generated from python API
(set-info :status unknown)
(declare-fun c () (_ BitVec 16))
(declare-fun b () (_ BitVec 16))
(declare-fun a () (_ BitVec 16))
(assert
 (let ((?x25 (bvmul ((_ extract 15 0) (ite (bvslt a (_ bv0 16)) (bvneg a) a)) ((_ zero_extend 13) ((_ extract 2 0) b)))))
(let (($x18 (and (distinct (ite (= (ite (bvsgt (_ bv65533 16) a) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) true)))
(let ((?x20 (ite (and (and (distinct (ite (bvsgt (_ bv4 16) a) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) true) $x18) (_ bv1 1) (_ bv0 1))))
(let ((?x24 (ite (and (distinct ?x20 (_ bv0 1)) true) (bvadd ((_ extract 15 0) ?x25) ((_ extract 15 0) c)) c)))
(and (distinct ?x24 ?x24) true))))))
(check-sat)
